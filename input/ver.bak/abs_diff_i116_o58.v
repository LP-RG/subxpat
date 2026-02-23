module abs_diff_i116_o58(a,b,r);
input [57:0] a,b;
output [57:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
