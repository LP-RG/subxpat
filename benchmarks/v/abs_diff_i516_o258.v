module abs_diff_i516_o258(a,b,r);
input [257:0] a,b;
output [257:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
