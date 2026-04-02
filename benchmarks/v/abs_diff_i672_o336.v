module abs_diff_i672_o336(a,b,r);
input [335:0] a,b;
output [335:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
