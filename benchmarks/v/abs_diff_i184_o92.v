module abs_diff_i184_o92(a,b,r);
input [91:0] a,b;
output [91:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
