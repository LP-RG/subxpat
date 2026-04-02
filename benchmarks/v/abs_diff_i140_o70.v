module abs_diff_i140_o70(a,b,r);
input [69:0] a,b;
output [69:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
