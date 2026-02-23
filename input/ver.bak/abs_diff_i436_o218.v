module abs_diff_i436_o218(a,b,r);
input [217:0] a,b;
output [217:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
