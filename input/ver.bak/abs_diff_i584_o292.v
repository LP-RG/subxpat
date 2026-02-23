module abs_diff_i584_o292(a,b,r);
input [291:0] a,b;
output [291:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
