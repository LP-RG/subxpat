module abs_diff_i172_o86(a,b,r);
input [85:0] a,b;
output [85:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
