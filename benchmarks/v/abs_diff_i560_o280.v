module abs_diff_i560_o280(a,b,r);
input [279:0] a,b;
output [279:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
