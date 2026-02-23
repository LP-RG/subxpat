module abs_diff_i616_o308(a,b,r);
input [307:0] a,b;
output [307:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
