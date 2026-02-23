module abs_diff_i748_o374(a,b,r);
input [373:0] a,b;
output [373:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
