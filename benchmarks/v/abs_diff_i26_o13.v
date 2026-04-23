module abs_diff_i26_o13(a,b,r);
input [12:0] a,b;
output [12:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
